import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from "@/components/ui/input";
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2, Plus, Trash2, Wifi, Tv, Coffee, Snowflake, Waves, Dumbbell, Car, Utensils, Star, CheckCircle } from 'lucide-react';
import apiClient from '@/api/client';
import { useToast } from "@/components/ui/use-toast";

// Types
interface Amenity {
    id: string;
    name: string;
    icon_slug: string;
    category: string;
    scope: 'hotel' | 'room';
    is_featured: boolean;
}

const ICONS: Record<string, any> = {
    wifi: Wifi,
    tv: Tv,
    coffee: Coffee,
    snowflake: Snowflake,
    waves: Waves,
    dumbbell: Dumbbell,
    car: Car,
    utensils: Utensils,
    star: Star
};

export default function Amenities() {
    const { toast } = useToast();
    const [amenities, setAmenities] = useState<Amenity[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        name: '',
        icon_slug: 'star',
        category: 'general',
        scope: 'room' as 'hotel' | 'room',
        is_featured: false
    });

    useEffect(() => {
        fetchAmenities();
    }, []);

    const fetchAmenities = async () => {
        setIsLoading(true);
        try {
            const data = await apiClient.get<Amenity[]>('/amenities');
            // If empty, try seeding defaults
            if (data.length === 0) {
                await apiClient.post('/amenities/seed-defaults');
                const seeded = await apiClient.get<Amenity[]>('/amenities');
                setAmenities(seeded);
            } else {
                setAmenities(data);
            }
        } catch (error) {
            toast({ variant: "destructive", title: "Error", description: "Failed to load amenities." });
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!formData.name) return;
        setIsSubmitting(true);
        try {
            const newAmenity = await apiClient.post<Amenity>('/amenities', formData);
            setAmenities([...amenities, newAmenity]);
            setIsDialogOpen(false);
            setFormData({ name: '', icon_slug: 'star', category: 'general', scope: 'room', is_featured: false });
            toast({ title: "Success", description: "Amenity created." });
        } catch (error) {
            toast({ variant: "destructive", title: "Error", description: "Failed to create amenity." });
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (id: string) => {
        try {
            await apiClient.delete(`/amenities/${id}`);
            setAmenities(amenities.filter(a => a.id !== id));
            toast({ title: "Deleted", description: "Amenity removed." });
        } catch (error) {
            toast({ variant: "destructive", title: "Error", description: "Failed to delete amenity." });
        }
    };

    const IconComponent = (slug: string) => {
        const Icon = ICONS[slug] || Star;
        return <Icon className="w-4 h-4" />;
    };

    return (
        <div className="p-6 space-y-6 max-w-6xl mx-auto">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Amenities Manager</h1>
                    <p className="text-slate-500 mt-2">Manage hotel features and room amenities.</p>
                </div>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                        <Button className="gap-2">
                            <Plus className="w-4 h-4" /> Add Amenity
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Add New Amenity</DialogTitle>
                            <DialogDescription>Create a new feature to highlight on your booking page.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label>Name</Label>
                                <Input
                                    placeholder="e.g. High-Speed WiFi"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Category</Label>
                                    <Select
                                        value={formData.category}
                                        onValueChange={(val) => setFormData({ ...formData, category: val })}
                                    >
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="general">General</SelectItem>
                                            <SelectItem value="tech">Technology</SelectItem>
                                            <SelectItem value="wellness">Wellness</SelectItem>
                                            <SelectItem value="dining">Dining</SelectItem>
                                            <SelectItem value="room">Room Feature</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Scope</Label>
                                    <Select
                                        value={formData.scope}
                                        onValueChange={(val) => setFormData({ ...formData, scope: val as 'hotel' | 'room' })}
                                    >
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="hotel">Hotel Level</SelectItem>
                                            <SelectItem value="room">Room Level</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Icon</Label>
                                    <Select
                                        value={formData.icon_slug}
                                        onValueChange={(val) => setFormData({ ...formData, icon_slug: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {Object.keys(ICONS).map(slug => (
                                                <SelectItem key={slug} value={slug}>
                                                    <div className="flex items-center gap-2">
                                                        {IconComponent(slug)} <span className="capitalize">{slug}</span>
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2 border p-3 rounded-md bg-slate-50">
                                <Switch
                                    checked={formData.is_featured}
                                    onCheckedChange={(checked) => setFormData({ ...formData, is_featured: checked })}
                                />
                                <div className="flex-1">
                                    <Label className="font-semibold">Featured Highlight?</Label>
                                    <p className="text-xs text-slate-500">Enable to show prominently on room cards.</p>
                                </div>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                            <Button onClick={handleCreate} disabled={isSubmitting}>
                                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Amenity"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Global Amenities Library</CardTitle>
                    <CardDescription>These amenities can be assigned to specific room types.</CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-10"><Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" /></div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[50px]">Icon</TableHead>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Category</TableHead>
                                    <TableHead>Scope</TableHead>
                                    <TableHead>Highlighted</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {amenities.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                                            No amenities found. Add one to get started.
                                        </TableCell>
                                    </TableRow>
                                ) : amenities.map((amenity) => (
                                    <TableRow key={amenity.id}>
                                        <TableCell>
                                            <div className="p-2 bg-slate-100 rounded-md inline-block text-slate-700">
                                                {IconComponent(amenity.icon_slug)}
                                            </div>
                                        </TableCell>
                                        <TableCell className="font-medium">{amenity.name}</TableCell>
                                        <TableCell><Badge variant="outline" className="capitalize">{amenity.category}</Badge></TableCell>
                                        <TableCell>
                                            <Badge variant={amenity.scope === 'hotel' ? 'default' : 'secondary'} className="capitalize">
                                                {amenity.scope}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            {amenity.is_featured && (
                                                <Badge variant="secondary" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                                                    Featured
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button size="icon" variant="ghost" className="text-red-500 hover:text-red-600 hover:bg-red-50" onClick={() => handleDelete(amenity.id)}>
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
