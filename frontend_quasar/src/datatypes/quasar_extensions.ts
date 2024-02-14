import {QTableColumn} from 'quasar';
import {Component} from 'vue';

interface CustomQTableColumn extends QTableColumn {
  // custom
  visible: boolean; // defines if the column is visible initially
  hideable?: boolean; // defines if the column can be hidden by the user (default: true)
  content?: Component; // defines the component to be used for rendering the column content
}

function convertToQTableColumn(customColumn: CustomQTableColumn): QTableColumn {
  // Use destructuring to omit the 'visible' property from the customColumn object
  const { visible, ...qTableColumn } = customColumn;

  // Return the remaining properties, which conform to the QTableColumn interface
  return qTableColumn;
}


export {convertToQTableColumn};
export type { CustomQTableColumn };
