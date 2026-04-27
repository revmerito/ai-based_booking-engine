import { Outlet, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { startTimeTracking, stopTimeTracking, trackEvent } from '@/lib/tracker';

export function PublicBookingLayout() {
    const { hotelSlug } = useParams();

    useEffect(() => {
        if (hotelSlug) {
            startTimeTracking(hotelSlug);
            trackEvent(hotelSlug, "page_view");
        }
        return () => {
            stopTimeTracking();
        };
    }, [hotelSlug]);

    return (
        <div className="min-h-screen bg-slate-50">
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex h-14 items-center justify-center">
                    <div className="font-bold text-xl tracking-tight text-primary">
                        Hotelier Hub <span className="text-muted-foreground text-sm font-normal">Secure Booking</span>
                    </div>
                </div>
            </header>
            <main className="container py-8">
                <Outlet />
            </main>
            <footer className="border-t py-6 md:py-0">
                <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
                    <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                        Powered by Hotelier Hub. Secure payments by Stripe.
                    </p>
                </div>
            </footer>
        </div>
    );
}
