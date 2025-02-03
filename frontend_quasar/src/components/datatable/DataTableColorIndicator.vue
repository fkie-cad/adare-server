<template>
  <q-chip
    :icon="icon"
    :color="color"
    square
    :clickable="false"
    :ripple="false"
    class="text-bold"
  />
</template>

<script lang="ts">
import { ref } from 'vue';
import { isValidStatusType, status_color_mapping, status_icon_mapping } from 'src/constants/mappings';

export default {
  name: 'DataTableColorIndicator',
  components: {  },
  props: {
    data: {
      type: Object,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
    col: {
      type: Object,
      required: true,
    },
  },

  setup(props) {
    const status = ref<string>(props.row[props.col.field].name);

    // Declare icon and color with default values
    let icon = 'mdi-help-circle';
    let color = 'grey';

    // Check if status is a valid StatusType
    if (isValidStatusType(status.value)) {
      icon = status_icon_mapping[status.value];
      color = status_color_mapping[status.value];
    }

    return {
      status,
      icon,
      color,
    };
  }

};
</script>
