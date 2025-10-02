import type { ComputedRef } from 'vue';

// Базовые типы
type Coord = { x: number; y: number };
type NullableCoord = { x: null; y: null };
type Legend = { color: string; name: string };

// Основные типы данных
type Dataset = {
  id: number | string;
  name: string;
  metrics: { id?: number | string; name: string; percents: number[] }[];
};

export type Segment = {
  id: string | number;
  name: string;
  color: string;
  pointCoords: (Coord | NullableCoord)[];
  pathCoords: { start: Coord | NullableCoord; end: Coord | NullableCoord }[];
};

type Tooltip = {
  name: string;
  metrics: { name: string; percent: number; color: string }[];
  position: Coord;
};

// Состояние
export interface InitialValue {
  columns: number;
  columnLabels: string[];
  legends: Legend[];
  datasetLabel: string;
  datasets: Dataset[];
}

export type ReactiveState = {
  axisYOrigin: number | null;
  columnsCoords: Coord[] | null;
  mouseCoords: Coord;
  hoveredSegment: { id: number; name: string } | null;
  highlightSegment: string | null;
  filterIdDataset: number | string;
  filterLegends: Legend[];
};

type ComputedState = {
  segments: ComputedRef<Segment[] | null>;
  tooltip: ComputedRef<Tooltip | null>;
};

export type State = {
  axis: ComputedRef<number[] | null>;
  gridlines: number[];
  columnWidth: number | null;
  reactive: ReactiveState;
  computed: ComputedState;
} & InitialValue;
