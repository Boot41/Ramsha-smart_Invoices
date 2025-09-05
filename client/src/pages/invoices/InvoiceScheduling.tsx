import React, { useState, useMemo, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Calendar, momentLocalizer, Views } from 'react-big-calendar';
import moment from 'moment';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { mockRentInvoiceSchedules, mockRentalAgreements } from '../../data/mockData';
import { invoiceSchedulerAPI, type ExtractedSchedule, type ScheduleExtractionResponse } from '../../../api/invoiceScheduler';
import type { RentInvoiceSchedule, RentalAgreement, SelectOption, RentInvoiceTemplate } from '../../../types';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const localizer = momentLocalizer(moment);

interface ScheduleEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  resource?: {
    schedule: RentInvoiceSchedule;
    agreement: RentalAgreement;
    type: 'invoice' | 'reminder';
  };
}

const InvoiceScheduling: React.FC = () => {
  const location = useLocation();
  const [selectedAgreement, setSelectedAgreement] = useState<RentalAgreement | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<RentInvoiceTemplate | null>(null);
  
  // Schedule extraction state
  const [extractedSchedules, setExtractedSchedules] = useState<ExtractedSchedule[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [extractionStats, setExtractionStats] = useState<{
    totalInvoices: number;
    processedInvoices: number;
    lastExtraction: string | null;
  }>({ totalInvoices: 0, processedInvoices: 0, lastExtraction: null });
  const [selectedExtractedSchedule, setSelectedExtractedSchedule] = useState<ExtractedSchedule | null>(null);
  const [showExtractionView, setShowExtractionView] = useState(false);

  useEffect(() => {
    // Get selected agreement and template from navigation state
    if (location.state?.selectedAgreement) {
      setSelectedAgreement(location.state.selectedAgreement as RentalAgreement);
    }
    if (location.state?.selectedTemplate) {
      setSelectedTemplate(location.state.selectedTemplate as RentInvoiceTemplate);
    }
  }, [location.state]);

  // Extract schedules from database invoices
  const handleExtractSchedules = async (userId?: string) => {
    setIsExtracting(true);
    setExtractionError(null);
    
    try {
      const response: ScheduleExtractionResponse = await invoiceSchedulerAPI.extractSchedules({
        user_id: userId
      });
      
      if (response.success) {
        setExtractedSchedules(response.schedule_extracts);
        setExtractionStats({
          totalInvoices: response.total_invoices,
          processedInvoices: response.processed_invoices,
          lastExtraction: response.extraction_timestamp
        });
        
        console.log('✅ Schedule extraction successful:', response);
      } else {
        setExtractionError(response.message || 'Failed to extract schedules');
      }
    } catch (error) {
      console.error('❌ Schedule extraction failed:', error);
      setExtractionError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setIsExtracting(false);
    }
  };
  const [schedules] = useState<RentInvoiceSchedule[]>(mockRentInvoiceSchedules);
  const [selectedSchedule, setSelectedSchedule] = useState<RentInvoiceSchedule | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newSchedule, setNewSchedule] = useState<Partial<RentInvoiceSchedule>>({
    frequency: 'monthly',
    reminderDays: [5, 1],
    autoGenerate: true,
    isActive: true
  });

  const frequencyOptions: SelectOption[] = [
    { value: 'monthly', label: 'Monthly' },
    { value: 'quarterly', label: 'Quarterly' },
    { value: 'annually', label: 'Annually' }
  ];

  const agreementOptions: SelectOption[] = mockRentalAgreements.map(agreement => ({
    value: agreement.id,
    label: `${agreement.propertyTitle} - ${agreement.tenantName}`
  }));

  // Generate calendar events from schedules and extracted data
  const calendarEvents = useMemo((): ScheduleEvent[] => {
    const events: ScheduleEvent[] = [];
    
    // Add events from existing mock schedules
    schedules.forEach(schedule => {
      const agreement = mockRentalAgreements.find(a => a.id === schedule.rentalAgreementId);
      if (!agreement) return;

      // Generate next 12 months of events
      const startDate = new Date(schedule.startDate);
      const endDate = schedule.endDate ? new Date(schedule.endDate) : new Date(Date.now() + 365 * 24 * 60 * 60 * 1000);
      
      let currentDate = new Date(startDate);
      let eventCount = 0;
      
      while (currentDate <= endDate && eventCount < 24) { // Limit events for performance
        // Invoice generation event
        const invoiceDate = new Date(currentDate);
        invoiceDate.setDate(currentDate.getDate() - 5); // Generate 5 days before due date
        
        if (invoiceDate >= new Date()) {
          events.push({
            id: `invoice-${schedule.id}-${eventCount}`,
            title: `📧 Generate Invoice: ${agreement.propertyTitle}`,
            start: invoiceDate,
            end: new Date(invoiceDate.getTime() + 60 * 60 * 1000), // 1 hour event
            resource: {
              schedule,
              agreement,
              type: 'invoice'
            }
          });
        }

        // Due date event
        events.push({
          id: `due-${schedule.id}-${eventCount}`,
          title: `💰 Rent Due: ${agreement.propertyTitle}`,
          start: new Date(currentDate),
          end: new Date(currentDate.getTime() + 60 * 60 * 1000),
          resource: {
            schedule,
            agreement,
            type: 'invoice'
          }
        });

        // Reminder events
        schedule.reminderDays.forEach((days, reminderIndex) => {
          const reminderDate = new Date(currentDate);
          reminderDate.setDate(currentDate.getDate() - days);
          
          if (reminderDate >= new Date()) {
            events.push({
              id: `reminder-${schedule.id}-${eventCount}-${reminderIndex}`,
              title: `⏰ Reminder: ${agreement.tenantName} (${days} days)`,
              start: reminderDate,
              end: new Date(reminderDate.getTime() + 30 * 60 * 1000), // 30 min event
              resource: {
                schedule,
                agreement,
                type: 'reminder'
              }
            });
          }
        });

        // Move to next period based on frequency
        switch (schedule.frequency) {
          case 'monthly':
            currentDate.setMonth(currentDate.getMonth() + 1);
            break;
          case 'quarterly':
            currentDate.setMonth(currentDate.getMonth() + 3);
            break;
          case 'annually':
            currentDate.setFullYear(currentDate.getFullYear() + 1);
            break;
        }
        eventCount++;
      }
    });

    // Add events from extracted schedules
    extractedSchedules.forEach((extractedSchedule, index) => {
      const scheduleDetails = extractedSchedule.schedule_details;
      
      if (scheduleDetails.found_schedule_info && scheduleDetails.send_dates?.length > 0) {
        scheduleDetails.send_dates.forEach((dateStr, dateIndex) => {
          try {
            const sendDate = new Date(dateStr);
            if (sendDate >= new Date()) {
              events.push({
                id: `extracted-${extractedSchedule.invoice_id}-${dateIndex}`,
                title: `🔄 ${extractedSchedule.client_name} - ${scheduleDetails.frequency || 'Scheduled'}`,
                start: sendDate,
                end: new Date(sendDate.getTime() + 60 * 60 * 1000),
                resource: {
                  extractedSchedule,
                  type: 'extracted'
                }
              });
            }
          } catch (error) {
            console.warn('Invalid date in extracted schedule:', dateStr);
          }
        });
      } else if (extractedSchedule.due_date) {
        // Fallback: use due date if available
        try {
          const dueDate = new Date(extractedSchedule.due_date);
          if (dueDate >= new Date()) {
            events.push({
              id: `extracted-due-${extractedSchedule.invoice_id}`,
              title: `💼 ${extractedSchedule.client_name} - Due`,
              start: dueDate,
              end: new Date(dueDate.getTime() + 60 * 60 * 1000),
              resource: {
                extractedSchedule,
                type: 'extracted'
              }
            });
          }
        } catch (error) {
          console.warn('Invalid due date in extracted schedule:', extractedSchedule.due_date);
        }
      }
    });

    return events;
  }, [schedules, extractedSchedules]);

  const eventStyleGetter = (event: ScheduleEvent) => {
    let backgroundColor = '#3b82f6';
    
    if (event.resource?.type === 'reminder') {
      backgroundColor = '#f59e0b';
    } else if (event.title.includes('Due')) {
      backgroundColor = '#dc2626';
    } else if (event.resource?.type === 'extracted') {
      backgroundColor = '#8b5cf6'; // Purple for extracted schedules
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block'
      }
    };
  };

  const handleCreateSchedule = () => {
    if (!newSchedule.rentalAgreementId || !newSchedule.startDate) {
      alert('Please fill in all required fields');
      return;
    }

    // Mock create logic
    console.log('Creating schedule:', newSchedule);
    alert('Schedule created successfully! (Mock implementation)');
    setShowCreateForm(false);
    setNewSchedule({
      frequency: 'monthly',
      reminderDays: [5, 1],
      autoGenerate: true,
      isActive: true
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Invoice Scheduling</h1>
          <p className="text-slate-600 mt-2">
            {selectedAgreement ? 
              `Managing schedule for ${selectedAgreement.propertyTitle}` :
              'Manage automated invoice generation and payment reminders'
            }
          </p>
          {extractionStats.lastExtraction && (
            <p className="text-sm text-slate-500 mt-1">
              Last extraction: {new Date(extractionStats.lastExtraction).toLocaleString()} 
              ({extractionStats.processedInvoices} of {extractionStats.totalInvoices} invoices processed)
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={() => handleExtractSchedules()} 
            variant="secondary"
            disabled={isExtracting}
            className="flex items-center gap-2"
          >
            {isExtracting ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                Extracting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Extract Schedules
              </>
            )}
          </Button>
          <Button 
            onClick={() => setShowExtractionView(!showExtractionView)} 
            variant="outline"
            className="flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {showExtractionView ? 'Hide' : 'View'} Extracted Data
          </Button>
          <Button 
            onClick={() => setShowCreateForm(true)} 
            variant="primary"
            className="flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Schedule
          </Button>
        </div>
      </div>

      {/* Extraction Error */}
      {extractionError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Extraction Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{extractionError}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Schedules Summary */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Total Schedules</p>
                <p className="text-2xl font-bold text-slate-900">{schedules.length}</p>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Active</p>
                <p className="text-2xl font-bold text-green-600">
                  {schedules.filter(s => s.isActive).length}
                </p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Next Invoice</p>
                <p className="text-sm font-bold text-slate-900">
                  {schedules.length > 0 ? new Date(schedules[0].nextSendDate).toLocaleDateString() : 'None'}
                </p>
              </div>
              <div className="p-2 bg-amber-100 rounded-lg">
                <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Monthly Revenue</p>
                <p className="text-lg font-bold text-slate-900">$15,600</p>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Extracted Schedules</p>
                <p className="text-2xl font-bold text-purple-600">
                  {extractedSchedules.length}
                </p>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice Schedule Calendar</CardTitle>
          <CardDescription>
            View all upcoming invoice generation dates, due dates, and reminders
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-600 rounded"></div>
              <span className="text-sm text-slate-600">Invoice Generation</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-600 rounded"></div>
              <span className="text-sm text-slate-600">Payment Due</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-amber-500 rounded"></div>
              <span className="text-sm text-slate-600">Reminder</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-purple-600 rounded"></div>
              <span className="text-sm text-slate-600">Extracted Schedule</span>
            </div>
          </div>
          
          <div style={{ height: '600px' }}>
            <Calendar
              localizer={localizer}
              events={calendarEvents}
              startAccessor="start"
              endAccessor="end"
              style={{ height: '100%' }}
              eventPropGetter={eventStyleGetter}
              views={[Views.MONTH, Views.WEEK, Views.DAY]}
              defaultView={Views.MONTH}
              popup
              onSelectEvent={(event) => {
                if (event.resource) {
                  if (event.resource.type === 'extracted') {
                    setSelectedExtractedSchedule(event.resource.extractedSchedule);
                    setSelectedSchedule(null);
                  } else {
                    setSelectedSchedule(event.resource.schedule);
                    setSelectedExtractedSchedule(null);
                  }
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Extracted Schedules View */}
      {showExtractionView && (
        <Card>
          <CardHeader>
            <CardTitle>Extracted Schedule Data</CardTitle>
            <CardDescription>
              Schedule details extracted from database invoices using RAG
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isExtracting ? (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-slate-600">Extracting schedule data...</span>
                </div>
              </div>
            ) : extractedSchedules.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <svg className="w-12 h-12 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No schedule data extracted yet</p>
                <p className="text-sm mt-1">Click "Extract Schedules" to analyze invoice data</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Summary */}
                <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-purple-900">
                      Found {extractedSchedules.filter(s => s.schedule_details.found_schedule_info).length} schedules
                      with AI-extracted data
                    </p>
                    <p className="text-xs text-purple-700 mt-1">
                      Average confidence: {(
                        extractedSchedules.reduce((sum, s) => sum + (s.schedule_details.confidence_score || 0), 0) / 
                        extractedSchedules.length
                      ).toFixed(2)}
                    </p>
                  </div>
                  <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                    {extractedSchedules.length} Total
                  </Badge>
                </div>

                {/* Extracted Schedules Grid */}
                <div className="grid gap-4 max-h-96 overflow-y-auto">
                  {extractedSchedules.map((schedule) => (
                    <Card 
                      key={schedule.invoice_id} 
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedExtractedSchedule?.invoice_id === schedule.invoice_id 
                          ? 'ring-2 ring-purple-500 bg-purple-50' 
                          : 'hover:bg-slate-50'
                      }`}
                      onClick={() => setSelectedExtractedSchedule(schedule)}
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-semibold text-slate-900">{schedule.client_name}</h4>
                              <Badge 
                                variant={schedule.schedule_details.found_schedule_info ? 'success' : 'secondary'}
                                className="text-xs"
                              >
                                {schedule.schedule_details.found_schedule_info ? 'Schedule Found' : 'Basic Info'}
                              </Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="text-slate-600">Invoice #:</span>
                                <span className="ml-2 font-mono">{schedule.invoice_number}</span>
                              </div>
                              <div>
                                <span className="text-slate-600">Amount:</span>
                                <span className="ml-2 font-semibold">
                                  ${schedule.total_amount?.toLocaleString() || 'N/A'} {schedule.currency}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Frequency:</span>
                                <span className="ml-2 capitalize">
                                  {schedule.schedule_details.frequency || 'Unknown'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Invoices:</span>
                                <span className="ml-2">
                                  {schedule.schedule_details.number_of_invoices || 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center gap-1 mb-1">
                              <svg className="w-3 h-3 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span className="text-xs text-purple-600 font-medium">
                                {((schedule.schedule_details.confidence_score || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-xs text-slate-500">
                              {schedule.schedule_details.extraction_method === 'rag_search' ? 'RAG' : 'Fallback'}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Extracted Schedule Details Sidebar */}
      {selectedExtractedSchedule && (
        <Card>
          <CardHeader>
            <CardTitle>Extracted Schedule Details</CardTitle>
            <CardDescription>
              AI-extracted data for {selectedExtractedSchedule.client_name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Basic Invoice Info */}
              <div>
                <h4 className="font-semibold text-slate-900 mb-3">Invoice Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="text-slate-600">Invoice Number</label>
                    <p className="font-mono">{selectedExtractedSchedule.invoice_number}</p>
                  </div>
                  <div>
                    <label className="text-slate-600">Contract ID</label>
                    <p className="font-mono text-xs">{selectedExtractedSchedule.contract_id}</p>
                  </div>
                  <div>
                    <label className="text-slate-600">Client Email</label>
                    <p className="text-blue-600">{selectedExtractedSchedule.client_email || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-slate-600">Status</label>
                    <Badge variant="secondary" className="capitalize">
                      {selectedExtractedSchedule.status}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Schedule Details */}
              <div>
                <h4 className="font-semibold text-slate-900 mb-3">Schedule Details</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Schedule Found</span>
                    <Badge 
                      variant={selectedExtractedSchedule.schedule_details.found_schedule_info ? 'success' : 'secondary'}
                    >
                      {selectedExtractedSchedule.schedule_details.found_schedule_info ? 'Yes' : 'No'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Frequency</span>
                    <span className="capitalize font-medium">
                      {selectedExtractedSchedule.schedule_details.frequency || 'Unknown'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Number of Invoices</span>
                    <span className="font-medium">
                      {selectedExtractedSchedule.schedule_details.number_of_invoices || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Confidence Score</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-purple-600 transition-all"
                          style={{ 
                            width: `${(selectedExtractedSchedule.schedule_details.confidence_score || 0) * 100}%` 
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">
                        {((selectedExtractedSchedule.schedule_details.confidence_score || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Send Dates */}
              {selectedExtractedSchedule.schedule_details.send_dates?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3">Send Dates</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedExtractedSchedule.schedule_details.send_dates.map((date, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {new Date(date).toLocaleDateString()}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Analysis Summary */}
              {selectedExtractedSchedule.schedule_details.analysis_summary && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3">AI Analysis</h4>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-700">
                      {selectedExtractedSchedule.schedule_details.analysis_summary}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex space-x-2">
            <Button variant="outline" size="sm">Create Schedule</Button>
            <Button variant="secondary" size="sm">View Invoice</Button>
            <Button variant="ghost" size="sm" onClick={() => setSelectedExtractedSchedule(null)}>Close</Button>
          </CardFooter>
        </Card>
      )}

      {/* Schedule Details Sidebar */}
      {selectedSchedule && (
        <Card>
          <CardHeader>
            <CardTitle>Schedule Details</CardTitle>
            <CardDescription>
              {mockRentalAgreements.find(a => a.id === selectedSchedule.rentalAgreementId)?.propertyTitle}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {(() => {
              const agreement = mockRentalAgreements.find(a => a.id === selectedSchedule.rentalAgreementId);
              return agreement ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-slate-600">Property</label>
                      <p className="text-slate-900">{agreement.propertyTitle}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-slate-600">Tenant</label>
                      <p className="text-slate-900">{agreement.tenantName}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-slate-600">Frequency</label>
                      <p className="text-slate-900 capitalize">{selectedSchedule.frequency}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-slate-600">Next Invoice</label>
                      <p className="text-slate-900">{new Date(selectedSchedule.nextSendDate).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-600">Reminder Days</label>
                    <div className="flex space-x-2 mt-1">
                      {selectedSchedule.reminderDays.map((days, index) => (
                        <Badge key={index} variant="secondary">{days} days before</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant={selectedSchedule.isActive ? 'success' : 'secondary'}>
                      {selectedSchedule.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                    <Badge variant={selectedSchedule.autoGenerate ? 'info' : 'secondary'}>
                      {selectedSchedule.autoGenerate ? 'Auto-Generate' : 'Manual'}
                    </Badge>
                  </div>
                </div>
              ) : null;
            })()}
          </CardContent>
          <CardFooter className="flex space-x-2">
            <Button variant="outline" size="sm">Edit Schedule</Button>
            <Button variant="secondary" size="sm">View Invoices</Button>
            <Button variant="ghost" size="sm" onClick={() => setSelectedSchedule(null)}>Close</Button>
          </CardFooter>
        </Card>
      )}

      {/* Create Schedule Form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create Invoice Schedule</CardTitle>
              <CardDescription>
                Set up automated invoice generation for a rental agreement
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Rental Agreement"
                  options={[{ value: '', label: 'Select agreement...' }, ...agreementOptions]}
                  value={newSchedule.rentalAgreementId || ''}
                  onChange={(value) => setNewSchedule(prev => ({ ...prev, rentalAgreementId: value }))}
                  required
                />
                <Select
                  label="Frequency"
                  options={frequencyOptions}
                  value={newSchedule.frequency || 'monthly'}
                  onChange={(value) => setNewSchedule(prev => ({ ...prev, frequency: value as any }))}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Start Date"
                  type="date"
                  value={newSchedule.startDate || ''}
                  onChange={(e) => setNewSchedule(prev => ({ ...prev, startDate: e.target.value }))}
                  required
                />
                <Input
                  label="End Date (Optional)"
                  type="date"
                  value={newSchedule.endDate || ''}
                  onChange={(e) => setNewSchedule(prev => ({ ...prev, endDate: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700 mb-2 block">
                  Reminder Days (days before due date)
                </label>
                <div className="flex space-x-2">
                  <Input
                    placeholder="e.g., 7"
                    className="flex-1"
                    onChange={(e) => {
                      const days = e.target.value.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d));
                      setNewSchedule(prev => ({ ...prev, reminderDays: days }));
                    }}
                  />
                  <span className="text-sm text-slate-500 self-center">Separate with commas</span>
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={newSchedule.autoGenerate}
                    onChange={(e) => setNewSchedule(prev => ({ ...prev, autoGenerate: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-700">Auto-generate invoices</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={newSchedule.isActive}
                    onChange={(e) => setNewSchedule(prev => ({ ...prev, isActive: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-700">Activate immediately</span>
                </label>
              </div>
            </CardContent>
            <CardFooter className="flex space-x-3">
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleCreateSchedule}>
                Create Schedule
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InvoiceScheduling;