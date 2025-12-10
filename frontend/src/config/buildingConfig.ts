export interface BuildingType {
    id: string;
    label: string;
    color: string;
    limit: number | null; // null means unlimited
    defaultCount: number;
    icon: string;
}

export const BUILDING_TYPES: Record<string, BuildingType> = {
    RECTORY: {
        id: 'Rectory',
        label: 'Rektörlük',
        color: '#9333ea', // Purple
        limit: 1,
        defaultCount: 0,
        icon: '🏛️'
    },
    DINING: {
        id: 'Dining',
        label: 'Yemekhane',
        color: '#f59e0b', // Amber
        limit: null,
        defaultCount: 1,
        icon: '🍽️'
    },
    FACULTY: {
        id: 'Faculty',
        label: 'Fakülte',
        color: '#3b82f6', // Blue
        limit: null,
        defaultCount: 2,
        icon: '🎓'
    },
    DORM: {
        id: 'Dormitory',
        label: 'Yurt',
        color: '#f97316', // Orange
        limit: null,
        defaultCount: 3,
        icon: '🛏️'
    },
    LIBRARY: {
        id: 'Library',
        label: 'Kütüphane',
        color: '#06b6d4', // Cyan
        limit: 1,
        defaultCount: 1,
        icon: '📚'
    },
    SPORTS: {
        id: 'Sports',
        label: 'Spor Merkezi',
        color: '#22c55e', // Green
        limit: null,
        defaultCount: 1,
        icon: '⚽'
    },
    LAB: {
        id: 'Research',
        label: 'Ar-Ge / Lab',
        color: '#ec4899', // Pink
        limit: null,
        defaultCount: 1,
        icon: '🔬'
    },
    SOCIAL: {
        id: 'Social',
        label: 'Sosyal Alan',
        color: '#e11d48', // Rose
        limit: null,
        defaultCount: 1,
        icon: '☕'
    }
};

// --- SMART HINTS (Research-Driven Data) ---
export const SMART_HINTS = {
    REGULATIONS: {
        TAKS: 0.40, // Base Area Ratio
        KAKS: 1.50, // Floor Area Ratio
        SETBACK: "Yoldan 5m, Komşudan 3m"
    }
};
