declare module 'react-json-tree' {
  import { ComponentType } from 'react';

  export interface Theme {
    scheme?: string;
    author?: string;
    base00?: string;
    base01?: string;
    base02?: string;
    base03?: string;
    base04?: string;
    base05?: string;
    base06?: string;
    base07?: string;
    base08?: string;
    base09?: string;
    base0A?: string;
    base0B?: string;
    base0C?: string;
    base0D?: string;
    base0E?: string;
    base0F?: string;
    extend?: Record<string, unknown>;
  }

  export interface JSONTreeProps {
    data: unknown;
    theme?: Theme;
    invertTheme?: boolean;
    hideRoot?: boolean;
    shouldExpandNodeInitially?: (
      keyPath: (string | number)[],
      data: unknown,
      level: number
    ) => boolean;
    labelRenderer?: (
      keyPath: (string | number)[],
      nodeType?: string,
      expanded?: boolean,
      expandable?: boolean
    ) => JSX.Element;
    valueRenderer?: (
      valueAsString: unknown,
      value: unknown,
      ...keyPath: (string | number)[]
    ) => JSX.Element;
    postprocessValue?: (value: unknown) => unknown;
    isCustomNode?: (value: unknown) => boolean;
    collectionLimit?: number;
    keyPath?: (string | number)[];
    sortObjectKeys?: boolean | ((a: string, b: string) => number);
    getItemString?: (
      type: string,
      data: unknown,
      itemType: string,
      itemString: string,
      keyPath: (string | number)[]
    ) => JSX.Element;
  }

  export const JSONTree: ComponentType<JSONTreeProps>;
}
