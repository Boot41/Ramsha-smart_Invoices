import { useState } from 'react';
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  Select,
  Textarea,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  type SelectOption
} from './ui';

// Icon components for demonstration
const PlusIcon = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);

const DownloadIcon = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

const StarIcon = () => (
  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

const ComponentShowcase = () => {
  const [selectedStatus, setSelectedStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const statusOptions: SelectOption[] = [
    { value: 'draft', label: 'Draft' },
    { value: 'sent', label: 'Sent' },
    { value: 'paid', label: 'Paid' },
    { value: 'overdue', label: 'Overdue' },
  ];

  const invoiceData = [
    { id: 'INV-001', client: 'Acme Corp', amount: '$2,500.00', status: 'paid', date: '2024-01-15' },
    { id: 'INV-002', client: 'Tech Solutions', amount: '$1,800.00', status: 'sent', date: '2024-01-20' },
    { id: 'INV-003', client: 'Design Studio', amount: '$3,200.00', status: 'overdue', date: '2024-01-10' },
    { id: 'INV-004', client: 'Marketing Plus', amount: '$950.00', status: 'draft', date: '2024-01-22' },
  ];

  const handleLoadingDemo = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen bg-background transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
      <div className="bg-gradient-to-br from-background via-background to-accent/5 min-h-screen">
        <div className="max-w-7xl mx-auto p-6 space-y-8">
          {/* Header with Dark Mode Toggle */}
          <header className="mb-12 text-center relative">
            <div className="absolute top-0 right-0">
              <Button variant="outline" onClick={toggleDarkMode} size="sm">
                {darkMode ? '🌞' : '🌙'} {darkMode ? 'Light' : 'Dark'}
              </Button>
            </div>
            <div className="bg-gradient-rainbow bg-clip-text text-transparent">
              <h1 className="text-6xl font-bold mb-4">Smart Invoice Scheduler</h1>
            </div>
            <p className="text-2xl text-muted-foreground mb-6">Modern UI Component Showcase</p>
            <div className="flex justify-center gap-4">
              <Badge variant="primary" size="lg">Design System</Badge>
              <Badge variant="success" size="lg">v2.0</Badge>
              <Badge variant="secondary" size="lg">Tailwind CSS</Badge>
            </div>
          </header>

          {/* Enhanced Buttons Section */}
          <Card hover shadow="xl" className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <span className="bg-gradient-primary bg-clip-text text-transparent">Button Variants</span>
                <Badge variant="success" size="sm">Live Demo</Badge>
              </CardTitle>
              <CardDescription>Comprehensive button system with variants, sizes, and interactive states</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              {/* Color Variants */}
              <div>
                <h3 className="text-lg font-semibold mb-4 text-foreground">Color Variants</h3>
                <div className="flex flex-wrap gap-4">
                  <Button variant="primary" leftIcon={<PlusIcon />}>Create Invoice</Button>
                  <Button variant="secondary">Save Draft</Button>
                  <Button variant="success">Mark Paid</Button>
                  <Button variant="warning">Send Reminder</Button>
                  <Button variant="error">Delete</Button>
                  <Button variant="outline">Cancel</Button>
                  <Button variant="ghost">View Details</Button>
                </div>
              </div>

              {/* Size & Shape Variants */}
              <div>
                <h3 className="text-lg font-semibold mb-4 text-foreground">Sizes & Shapes</h3>
                <div className="flex flex-wrap items-center gap-4 mb-4">
                  <Button size="xs" variant="primary">Extra Small</Button>
                  <Button size="sm" variant="primary">Small</Button>
                  <Button size="md" variant="primary">Medium</Button>
                  <Button size="lg" variant="primary">Large</Button>
                  <Button size="xl" variant="primary">Extra Large</Button>
                </div>
                <div className="flex flex-wrap gap-4">
                  <Button rounded="none" variant="secondary">Square</Button>
                  <Button rounded="sm" variant="secondary">Small Rounded</Button>
                  <Button rounded="md" variant="secondary">Medium Rounded</Button>
                  <Button rounded="lg" variant="secondary">Large Rounded</Button>
                  <Button rounded="full" variant="secondary">Pill Shape</Button>
                </div>
              </div>

              {/* Interactive States */}
              <div>
                <h3 className="text-lg font-semibold mb-4 text-foreground">Interactive States</h3>
                <div className="flex flex-wrap gap-4">
                  <Button loading={loading} onClick={handleLoadingDemo} variant="primary">
                    {loading ? 'Processing...' : 'Process Payment'}
                  </Button>
                  <Button disabled variant="secondary">Disabled State</Button>
                  <Button shadow="lg" variant="success" leftIcon={<DownloadIcon />}>
                    Download Report
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Badges Section */}
          <Card hover shadow="lg" className="mb-8">
            <CardHeader>
              <CardTitle>Status Badges & Indicators</CardTitle>
              <CardDescription>Visual indicators for different invoice statuses and system states</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4 text-foreground">Status Variants</h3>
                <div className="flex flex-wrap gap-4">
                  <Badge variant="primary">New</Badge>
                  <Badge variant="secondary">Draft</Badge>
                  <Badge variant="success">Paid</Badge>
                  <Badge variant="warning">Pending</Badge>
                  <Badge variant="error">Overdue</Badge>
                  <Badge variant="outline">Cancelled</Badge>
                  <Badge variant="info">Processing</Badge>
                  <Badge variant="purple">Premium</Badge>
                  <Badge variant="orange">Urgent</Badge>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-4 text-foreground">Badge Sizes</h3>
                <div className="flex flex-wrap items-center gap-4">
                  <Badge variant="success" size="sm">Small</Badge>
                  <Badge variant="warning" size="md">Medium</Badge>
                  <Badge variant="error" size="lg">Large</Badge>
                  <Badge variant="purple" size="md">VIP Client</Badge>
                  <Badge variant="info" size="sm">Auto-Pay</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Form Components */}
          <Card glass hover shadow="xl" className="mb-8">
            <CardHeader>
            <CardTitle>Form Components</CardTitle>
            <CardDescription>Input fields for invoice and client information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Client Name"
                placeholder="Enter client name"
                hint="The name of your client or company"
              />
              <Input
                label="Invoice Amount"
                type="number"
                placeholder="0.00"
                hint="Amount in USD"
              />
              <Input
                label="Due Date"
                type="date"
              />
              <Select
                label="Invoice Status"
                options={statusOptions}
                placeholder="Select status"
                value={selectedStatus}
                onChange={setSelectedStatus}
                hint="Current status of the invoice"
              />
            </div>
            <Textarea
              label="Description"
              placeholder="Enter invoice description or notes..."
              hint="Optional description for the invoice"
              rows={4}
            />
            <Input
              label="Email Address"
              type="email"
              placeholder="client@example.com"
              error="Please enter a valid email address"
            />
          </CardContent>
        </Card>

        {/* Badges Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Status Badges</CardTitle>
            <CardDescription>Visual indicators for different invoice statuses</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-4">
              <Badge variant="primary">New</Badge>
              <Badge variant="secondary">Draft</Badge>
              <Badge variant="success">Paid</Badge>
              <Badge variant="warning">Pending</Badge>
              <Badge variant="error">Overdue</Badge>
              <Badge variant="outline">Cancelled</Badge>
            </div>
            <div className="flex flex-wrap gap-4">
              <Badge variant="success" size="sm">Paid</Badge>
              <Badge variant="warning" size="md">Due Soon</Badge>
              <Badge variant="error" size="lg">30 Days Overdue</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Table Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Invoice Management Table</CardTitle>
            <CardDescription>Overview of all invoices with their current status</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice ID</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoiceData.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell className="font-mono">{invoice.id}</TableCell>
                    <TableCell className="font-medium">{invoice.client}</TableCell>
                    <TableCell className="font-semibold">{invoice.amount}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          invoice.status === 'paid' ? 'success' :
                          invoice.status === 'sent' ? 'primary' :
                          invoice.status === 'overdue' ? 'error' : 'secondary'
                        }
                      >
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>{invoice.date}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm">View</Button>
                        <Button variant="ghost" size="sm">Edit</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="justify-between">
            <p className="text-sm text-muted-foreground">Showing 4 of 4 invoices</p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">Previous</Button>
              <Button variant="outline" size="sm">Next</Button>
            </div>
          </CardFooter>
        </Card>

          {/* Enhanced Dashboard Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <Card hover gradient shadow="xl" className="group">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="bg-gradient-success bg-clip-text text-transparent">Total Revenue</span>
                  <Badge variant="success">+12%</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-bold text-success-600 group-hover:scale-105 transition-transform">$8,450.00</p>
                <p className="text-sm text-muted-foreground mt-1">This month</p>
              </CardContent>
            </Card>

            <Card hover shadow="xl" className="group border-warning-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="text-warning-700">Pending Invoices</span>
                  <Badge variant="warning">3</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-bold text-warning-600 group-hover:scale-105 transition-transform">$4,750.00</p>
                <p className="text-sm text-muted-foreground mt-1">Awaiting payment</p>
              </CardContent>
            </Card>

            <Card hover shadow="xl" className="group border-error-200 bg-gradient-to-br from-card to-error-50/10">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="text-error-700">Overdue Amount</span>
                  <Badge variant="error">2</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-bold text-error-600 group-hover:scale-105 transition-transform">$3,200.00</p>
                <p className="text-sm text-muted-foreground mt-1">Requires attention</p>
              </CardContent>
              <CardFooter>
                <Button variant="error" size="sm" fullWidth leftIcon={<StarIcon />}>
                  Send Reminders
                </Button>
              </CardFooter>
            </Card>
          </div>

          {/* Enhanced Quick Actions */}
          <Card hover shadow="2xl" className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <span className="bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                  Quick Actions
                </span>
                <Badge variant="primary" size="sm">Pro Tools</Badge>
              </CardTitle>
              <CardDescription>Common tasks and shortcuts for efficient invoice management</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button variant="primary" fullWidth leftIcon={<PlusIcon />} shadow="md">
                  New Invoice
                </Button>
                <Button variant="secondary" fullWidth shadow="sm">
                  Import Clients
                </Button>
                <Button variant="outline" fullWidth rightIcon={<DownloadIcon />}>
                  Export Reports
                </Button>
                <Button variant="ghost" fullWidth>
                  Settings
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Feature Showcase Footer */}
          <Card gradient shadow="2xl" className="text-center">
            <CardContent className="py-12">
              <div className="bg-gradient-rainbow bg-clip-text text-transparent mb-6">
                <h2 className="text-4xl font-bold">Modern Design System</h2>
              </div>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Built with Tailwind CSS, featuring comprehensive component variants, 
                interactive states, and seamless dark mode support.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Button variant="primary" size="lg" leftIcon={<StarIcon />} shadow="xl">
                  Get Started
                </Button>
                <Button variant="outline" size="lg" rightIcon={<DownloadIcon />}>
                  View Documentation
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ComponentShowcase;