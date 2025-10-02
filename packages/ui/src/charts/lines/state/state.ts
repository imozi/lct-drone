import { computed, reactive, readonly, type InjectionKey } from 'vue';

import { useAdjustCoordinates } from '../composables/useAdjustCoordinates';

import type { InitialValue, ReactiveState, Segment, State } from '../types';

export const createState = (initialValue: InitialValue) => {
  const datasets = new Map(initialValue.datasets.map((dataset) => [dataset.id, dataset]));
  const legends = new Map(initialValue.legends.map((legend) => [legend.name, legend]));

  const minValue = 0;

  const reactiveState = reactive<ReactiveState>({
    axisYOrigin: null,
    columnsCoords: null,
    mouseCoords: { x: -1, y: -1 },
    hoveredSegment: null,
    highlightSegment: null,
    filterIdDataset: initialValue.datasets[0].id,
    filterLegends: initialValue.legends.slice(0, 5),
  });

  const isMetricFiltered = (metricName: string): boolean => {
    return reactiveState.filterLegends.some((legend) => legend.name === metricName);
  };

  const maxValue = computed(() => {
    const dataset = datasets.get(reactiveState.filterIdDataset);
    if (!dataset) return 100;

    const values = dataset.metrics.flatMap((metric) => {
      const isSelected = reactiveState.filterLegends.some((legend) => legend.name === metric.name);
      if (isSelected) {
        return metric.percents.filter((percent) => percent !== null);
      }
      return [];
    });
    return values.length ? Math.max(...values) : 100;
  });

  // Делаем axisValues вычисляемым свойством
  const axisValues = computed(() => {
    return [
      Math.ceil(maxValue.value),
      Math.ceil((3 * maxValue.value) / 4),
      Math.ceil((2 * maxValue.value) / 4),
      Math.ceil(maxValue.value / 4),
      minValue,
    ];
  });

  const segments = computed(() => {
    if (!reactiveState.columnsCoords) return null;

    const dataset = datasets.get(reactiveState.filterIdDataset);
    if (!dataset) return null;

    return dataset.metrics.reduce((acc, metric, i) => {
      if (!isMetricFiltered(metric.name)) {
        return acc;
      }

      const pointCoords = metric.percents.map((percent, j) => {
        if (percent === null) return { x: null, y: null };

        const normalizedPercent = (percent / maxValue.value) * 100;

        return useAdjustCoordinates({
          x: reactiveState.columnsCoords![j].x,
          y: normalizedPercent,
          center: reactiveState.axisYOrigin ?? 0,
          axis: 'y',
        });
      });

      const pathCoords = pointCoords.slice(0, -1).map((coord, j) => {
        return {
          start: coord,
          end: pointCoords[j + 1],
        };
      });

      acc.push({
        id: metric.id ?? `${i}-${dataset.id}-${dataset.name}`,
        name: metric.name,
        color: legends.get(metric.name)?.color ?? '#000000',
        pointCoords,
        pathCoords,
      });

      return acc;
    }, [] as Segment[]);
  });

  const tooltip = computed(() => {
    if (!reactiveState.columnsCoords || !reactiveState.hoveredSegment) {
      return null;
    }

    const dataset = datasets.get(reactiveState.filterIdDataset);
    if (!dataset) return null;

    const metrics = dataset.metrics
      .filter((metric) => isMetricFiltered(metric.name))
      .map((metric) => ({
        name: metric.name,
        percent: metric.percents[reactiveState.hoveredSegment!.id],
        color: legends.get(metric.name)?.color ?? '#000000',
      }));

    return {
      name: reactiveState.hoveredSegment.name,
      metrics,
      position: reactiveState.columnsCoords[reactiveState.hoveredSegment.id],
    };
  });

  const state: State = {
    axis: axisValues,
    gridlines: [0, 25, 50, 75, 100],
    columns: initialValue.columns,
    columnWidth: null,
    columnLabels: initialValue.columnLabels,
    legends: initialValue.legends,
    datasetLabel: initialValue.datasetLabel,
    datasets: initialValue.datasets,
    reactive: reactiveState,
    computed: {
      segments,
      tooltip,
    },
  };

  const createUpdater = <T extends object, K extends keyof T>(target: T, key: K, transform?: (value: T[K]) => T[K]) => {
    return (newValue: T[K]) => {
      target[key] = transform ? transform(newValue) : newValue;
    };
  };

  const actions = {
    updateAxisYOrigin: createUpdater(reactiveState, 'axisYOrigin'),
    updateColumnsCoords: createUpdater(reactiveState, 'columnsCoords'),
    updateColumnWidth: createUpdater(state, 'columnWidth'),
    updateMouseCoords: createUpdater(reactiveState, 'mouseCoords'),
    resetMouseCoords: () => createUpdater(reactiveState, 'mouseCoords')({ x: -1, y: -1 }),
    updateHoveredSegment: createUpdater(reactiveState, 'hoveredSegment'),
    resetHoveredSegment: () => createUpdater(reactiveState, 'hoveredSegment')(null),
    updateHighlightSegment: createUpdater(reactiveState, 'highlightSegment'),
    resetHighlightSegment: () => createUpdater(reactiveState, 'highlightSegment')(null),
    updateIdDataset: createUpdater(reactiveState, 'filterIdDataset'),
    updateFilterLegend: (name: string) => {
      const setLegends = new Set(reactiveState.filterLegends.map((legend) => legend.name));
      if (setLegends.has(name)) {
        setLegends.delete(name);
      } else {
        setLegends.add(name);
      }
      reactiveState.filterLegends = state.legends.filter((legend) => setLegends.has(legend.name));
    },
  };

  return {
    state: readonly(state),
    actions,
  };
};

export const stateKey: InjectionKey<ReturnType<typeof createState>> = Symbol('chart-line-store');
