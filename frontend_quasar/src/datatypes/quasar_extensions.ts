import {QTableColumn} from 'quasar';
import {Component} from 'vue';

interface TypeVarsDetails {
  field: string;
  formatter?: (value: string | undefined) => string;
  icon?: string;
  color?: string;
}

interface TypeVarsLink {
  icon?: string;
  tooltip?: string;
  color?: string;
}

interface CustomQTableColumn extends QTableColumn {
  // custom
  visible?: boolean; // defines if the column is visible initially
  hideable?: boolean; // defines if the column can be hidden by the user (default: true)
  type?: Component; // defines the component to be used for rendering the column content
  // properties for type details
  typeVarsDetails?: TypeVarsDetails;
  // properties for type link
  typeVarsLink?: TypeVarsLink;
}

export type { TypeVarsDetails, TypeVarsLink, CustomQTableColumn };
