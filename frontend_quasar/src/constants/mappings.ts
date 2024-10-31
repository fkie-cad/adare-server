export const request_obj_icon_mapping = {
  experiment: 'o_science',
  environment: 'o_terrain',
  testfunctionset: 'o_quiz',
};

// Define the status list and create a union type
export const statusList = [
  'not assigned',
  'accepted',
  'rejected',
  'assigned',
  'success',
] as const;
export type StatusType = typeof statusList[number];

export function isValidStatusType(value: string): value is StatusType {
    return (statusList as readonly string[]).includes(value);
}

// Use the StatusType for the mappings
export const status_color_mapping: Record<StatusType, string> = {
  'not assigned': 'blue',
  accepted: 'positive',
  rejected: 'negative',
  assigned: 'warning',
  success: 'green',
};

export const status_icon_mapping: Record<StatusType, string> = {
  'not assigned': 'o_info',
  accepted: 'o_check',
  rejected: 'o_close',
  assigned: 'o_pending',
  success: 'o_done',
};

export const osList = ['windows', 'linux'] as const;

// Create a union type based on the elements of osList
export type OSListType = typeof osList[number];

export function isValidOSListType(value: string): value is OSListType {
    return (osList as readonly string[]).includes(value);
}

export const os_icon_mapping: Record<OSListType, string> = {
  windows: 'windows',
  linux: 'unix',
};

export const os_color_mapping: Record<OSListType, string> = {
  windows: 'blue',
  linux: 'black',
};


