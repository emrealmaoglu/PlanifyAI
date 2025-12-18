import { useEffect } from 'react';
import { useMapContext } from './MapContext';

interface InitialContextFetcherProps {
    onInitialCenter: (lat: number, lon: number) => void;
}

/**
 * InitialContextFetcher
 * - Harita yüklendiğinde current center'ı alır
 * - Parent'e callback ile bildirir (ör: fetchContextWithUI)
 */
export const InitialContextFetcher: React.FC<InitialContextFetcherProps> = ({
    onInitialCenter
}) => {
    const { map, isMapLoaded } = useMapContext();

    useEffect(() => {
        if (!map || !isMapLoaded) return;

        const center = map.getCenter();
        if (!center) return;

        console.log(
            'InitialContextFetcher → triggering context fetch for:',
            center.lat,
            center.lng
        );

        // Promise dönse bile burada await etmeye gerek yok
        onInitialCenter(center.lat, center.lng);
    }, [map, isMapLoaded, onInitialCenter]);

    return null;
};
