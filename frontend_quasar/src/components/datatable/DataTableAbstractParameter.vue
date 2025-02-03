<template>
  <q-chip
    v-for="param in data"
    :key="param.name"
    :label="param.name"
    :clickable="false"
    :ripple="false"
    square
    :color="getParamColor(param)"
  >
    <q-tooltip v-if="param.description">
      {{ param.description }}
    </q-tooltip>
  </q-chip>
</template>

<script lang="ts">
import { AbstractParameter } from 'src/models/experiment';
import { dtype_color_mapping, isValidDtype } from 'src/constants/mappings';

export default {
  name: 'DataTableAbstractParameter',
  components: {  },
  props: {
    data: {
      type: Object as () => AbstractParameter[],
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

  setup() {

    function getParamColor(param: AbstractParameter) {
      if (isValidDtype(param.dtype)) {
        return dtype_color_mapping[param.dtype];
      }
      return 'grey';
    }


    return {
      getParamColor,
    };
  }

};
</script>
