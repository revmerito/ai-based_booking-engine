import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";

// Auth Pages
import LoginPage from "@/pages/auth/Login";
import SignupPage from "@/pages/auth/Signup";
import OnboardingPage from "@/pages/auth/Onboarding";
import ForgotPasswordPage from "@/pages/auth/ForgotPassword";

import ResetPasswordPage from "@/pages/auth/ResetPassword";

// Dashboard Layout & Pages
// Dashboard Layout & Pages
import DashboardLayout from "@/components/layout/DashboardLayout";
import DashboardPage from "@/pages/dashboard/Dashboard";
import RoomsPage from "@/pages/rooms/Rooms";
import RatesPage from "@/pages/finance/Rates";
import AvailabilityPage from "@/pages/rooms/Availability";
import BookingsPage from "@/pages/bookings/Bookings";
import GuestsPage from "@/pages/bookings/Guests";
import PaymentsPage from "@/pages/finance/Payments";
import ReportsPage from "@/pages/finance/Reports";
import AddonsPage from "@/pages/marketing/Addons";
import SettingsPage from "@/pages/settings/Settings";
import IntegrationPage from "@/pages/settings/Integration";
import ChannelSettings from '@/pages/dashboard/ChannelSettings';
import Amenities from '@/pages/dashboard/Amenities';
import RatesShopper from "@/pages/marketing/RatesShopper";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import AgentPage from "@/pages/agent/AgentPage";
import ProfilePage from "@/pages/settings/Profile";



import NotFound from "@/pages/NotFound";

import { PublicBookingLayout } from "@/layouts/PublicBookingLayout";
import BookingSelection from "@/pages/public/BookingSelection";
import BookingCheckout from "@/pages/public/BookingCheckout";
import BookingConfirmation from "@/pages/public/BookingConfirmation";
import BookingWidget from "@/pages/public/BookingWidget";
import ChatEmbed from "@/pages/public/ChatEmbed";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />


            {/* Protected Dashboard Routes */}
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/rooms" element={<RoomsPage />} />
              <Route path="/rates" element={<RatesPage />} />
              <Route path="/availability" element={<AvailabilityPage />} />
              <Route path="/bookings" element={<BookingsPage />} />
              <Route path="/guests" element={<GuestsPage />} />
              <Route path="/rate-shopper" element={<RatesShopper />} />
              <Route path="/payments" element={<PaymentsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/addons" element={<AddonsPage />} />
              <Route path="/amenities" element={<Amenities />} />
              <Route path="/channel-settings" element={<ChannelSettings />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/integration" element={<IntegrationPage />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/agent" element={<AgentPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>

            {/* Public Booking Engine Routes */}
            <Route path="/book/:hotelSlug" element={<PublicBookingLayout />}>
              <Route index element={<Navigate to="rooms" replace />} />
              <Route path="rooms" element={<BookingSelection />} />
              <Route path="checkout" element={<BookingCheckout />} />
              <Route path="confirmation" element={<BookingConfirmation />} />
            </Route>

            {/* Standalone Widget Route */}
            <Route path="/book/:hotelSlug/widget" element={<BookingWidget />} />
            <Route path="/book/:hotelSlug/chat" element={<ChatEmbed />} />

            {/* Redirects */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
