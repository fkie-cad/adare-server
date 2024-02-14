
// implements quasar QTableColumn (QTableProps['columns'])
interface QTableColumn {
  name: string;
  label: string;
  field: string | ((row: object) => any);
  required?: boolean;
  align?: 'left'|'center'|'right'|undefined;
  sortable?: boolean;
  sort?: (a: any, b: any, rowA: object, rowB: object) => number;
  rawSort?: (a: any, b: any, rowA: object, rowB: object) => number;
  sortOrder?: 'ad'|'da'|undefined;
  format?: (val: any, row: object) => any;
  style?: string | ((row: object) => string);
  classes?: string | ((row: object) => string);
  headerStyle?: string;
  headerClasses?: string;
}

interface QTablePagination {
  sortBy: string | null;
  descending: boolean;
  page: number;
  rowsPerPage: number;
  rowsNumber: number;
}

export type { QTableColumn, QTablePagination };
