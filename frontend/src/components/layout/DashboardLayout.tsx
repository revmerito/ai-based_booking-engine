// Main Dashboard Layout - wraps all authenticated pages
import { Outlet, Navigate } from 'react-router-dom';
import { LayoutDashboard, Calendar, BedDouble, Users, Settings, LogOut, Menu, X, Receipt, Link2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { Skeleton } from '@/components/ui/skeleton';

export function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading skeleton while checking auth
  if (isLoading) {
    return (
      <div className="flex h-screen w-full">
        {/* Sidebar skeleton */}
        <div className="hidden w-64 flex-col gap-4 border-r bg-sidebar p-4 md:flex">
          <Skeleton className="h-10 w-full" />
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </div>
        {/* Main content skeleton */}
        <div className="flex flex-1 flex-col">
          <Skeleton className="h-16 w-full" />
          <div className="flex-1 space-y-4 p-6">
            <Skeleton className="h-8 w-48" />
            <div className="grid gap-4 md:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  const { user } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }



  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <SidebarInset className="flex flex-1 flex-col">
          <AppHeader />
          <main className="flex-1 overflow-auto p-4 md:p-6">
            <Outlet />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}

export default DashboardLayout;
