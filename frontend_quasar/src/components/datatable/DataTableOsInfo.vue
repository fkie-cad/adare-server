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
import { ref } from 'vue';
import { isValidOSListType, os_icon_mapping, os_color_mapping } from 'src/constants/mappings';

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
    const os = ref<string>(props.data.os);


    let os_icon = 'mdi-help-circle';
    let os_color = 'grey';

    if (isValidOSListType(os.value)) {
      os_icon = os_icon_mapping[os.value];
      os_color = os_color_mapping[os.value];
    }

    return {
      os_icon,
      os_color,
    };
  }
};
</script>
