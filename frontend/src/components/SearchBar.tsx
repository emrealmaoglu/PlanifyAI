import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useOptimizationStore } from '../store/useOptimizationStore';
import { config } from '../config';

export function SearchBar() {
    const [query, setQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const { setPreviewContext, setBoundary } = useOptimizationStore();

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsSearching(true);
        try {
            const response = await fetch(`${config.apiBaseUrl}/api/optimize/context/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Search failed');
            }

            // Update store with preview data
            setPreviewContext(data.data);

            // Auto-set boundary from the search result if available
            // The boundary is in the 'boundary' layer of the GeoJSON
            const boundaryFeature = data.data.features.find((f: any) => f.properties.layer === 'boundary');
            if (boundaryFeature && boundaryFeature.geometry.type === 'Polygon') {
                // Convert GeoJSON coordinates (lng, lat) to our Point format {x, y}
                const coords = boundaryFeature.geometry.coordinates[0];
                const points = coords.map((c: number[]) => ({ x: c[0], y: c[1] }));
                // Remove last point if it duplicates the first (GeoJSON standard)
                if (points.length > 0 &&
                    points[0].x === points[points.length - 1].x &&
                    points[0].y === points[points.length - 1].y) {
                    points.pop();
                }
                setBoundary(points);
            }

        } catch (error) {
            console.error('Search failed:', error);
            alert('Search failed: ' + (error as Error).message);
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <form onSubmit={handleSearch} className="relative mb-4">
            <div className="relative flex items-center">
                <Search className="absolute left-3 text-gray-400" size={20} />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search location (e.g. Kastamonu University)"
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
                <button
                    type="submit"
                    disabled={isSearching || !query.trim()}
                    className="absolute right-2 bg-blue-600 text-white p-1.5 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition"
                >
                    {isSearching ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
                </button>
            </div>
        </form>
    );
}
