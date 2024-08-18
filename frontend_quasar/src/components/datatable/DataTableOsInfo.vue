<template>
  <div>
    <q-icon :name="os_icon" :color="os_color"></q-icon>
    <span class="q-ml-xs">{{ data.distribution }}</span>
    <q-tooltip >
      <div class="text-body2">OS: {{ data.os }}</div>
      <div class="text-body2">Distribution: {{ data.distribution }}</div>
      <div class="text-body2">Version: {{ data.version }}</div>
      <div class="text-body2" v-if="data.language">Language: {{ data.language }}</div>
      <div class="text-body2" v-if="data.architecture">Architecture: {{ data.architecture }}</div>
      <div class="text-body2" v-if="data.details">Details: {{ data.details }}</div>
    </q-tooltip>
  </div>
</template>

<script lang="ts">
import { os_icon_mapping, os_color_mapping } from 'src/constants/mappings';

export default {
  name: 'DataTableOsInfo',
  components: {  },
  props: {
    data: {
      type: Object,
      required: true,
    },
  },

  setup(props) {

    // get icon for os (by taking lowercase os name and looking up in os_icon_mapping) (no color and no icon if not found)
    const os_icon = os_icon_mapping[props.data.os.toLowerCase()] || 'mdi-help';
    // get color for os (by taking lowercase os name and looking up in os_color_mapping) (no color and no icon if not found)
    const os_color = os_color_mapping[props.data.os.toLowerCase()] || 'black';

    return {
      os_icon,
      os_color,
    };
  }
};
</script>
