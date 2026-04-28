import { Check, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';

interface BookingStepperProps {
    currentStep: 1 | 2 | 3 | 4;
}

export function BookingStepper({ currentStep }: BookingStepperProps) {
    const { hotelSlug } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    // Helper to get search params from location to preserve state when clicking back
    const [searchParams] = useSearchParams();
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';

    const steps = [
        { id: 1, label: 'Search', path: `/book/${hotelSlug}/rooms${queryString}` }, // Redirects to rooms effectively
        { id: 2, label: 'Select Rooms', path: `/book/${hotelSlug}/rooms${queryString}` },
        { id: 3, label: 'Enhance Stay', path: null },
        { id: 4, label: 'Guest Info', path: `/book/${hotelSlug}/checkout${queryString}` },
    ];

    return (
        <div className="w-full bg-white border-b border-slate-200 shadow-sm mb-6">
            <div className="max-w-7xl mx-auto">
                <div className="grid grid-cols-4 divide-x divide-slate-100">
                    {steps.map((step) => {
                        const isActive = step.id === currentStep;
                        const isCompleted = step.id < currentStep;
                        const isClickable = isCompleted && step.path;

                        return (
                            <div
                                key={step.id}
                                className={cn(
                                    "relative flex items-center justify-center p-3 md:p-4 text-sm font-medium transition-colors select-none",
                                    isActive ? "bg-slate-800 text-white" : "bg-white text-slate-500",
                                    isClickable ? "cursor-pointer hover:bg-slate-50" : "cursor-default"
                                )}
                                onClick={() => {
                                    if (isClickable && step.path) {
                                        navigate(step.path);
                                    }
                                }}
                            >
                                <div className="flex items-center gap-2">
                                    <div className={cn(
                                        "flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold border",
                                        isActive ? "border-white bg-white text-slate-900" :
                                            isCompleted ? "border-green-600 bg-green-600 text-white" : "border-slate-300 bg-slate-100 text-slate-400"
                                    )}>
                                        {isCompleted ? <Check className="w-3.5 h-3.5" /> : step.id}
                                    </div>
                                    <span className={cn("hidden md:inline", isActive || isCompleted ? "font-bold" : "font-medium")}>
                                        {step.label}
                                    </span>
                                </div>

                                {/* Arrow pointer for active step */}
                                {isActive && (
                                    <div className="absolute -bottom-[9px] left-1/2 -translate-x-1/2 w-4 h-4 bg-slate-800 rotate-45 border-r border-b border-white hidden md:block z-10" />
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Context Bar */}
            {currentStep > 1 && (
                <div className="bg-slate-50 border-b border-slate-200 py-2">
                    <div className="max-w-7xl mx-auto px-4 flex justify-between items-center text-xs md:text-sm">
                        <div className="flex items-center gap-4 text-slate-600">
                            <span className="font-bold text-slate-900 flex items-center">
                                <MapPin className="w-3.5 h-3.5 mr-1" />
                                {hotelSlug?.replace(/-/g, ' ').toUpperCase() || 'STAYBOOKER'}
                            </span>
                        </div>
                        <div className="flex gap-4">
                            <button className="text-primary font-semibold hover:underline" onClick={() => document.getElementById('search-bar')?.scrollIntoView({ behavior: 'smooth' })}>
                                Modify Search
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
