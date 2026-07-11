<template>
  <div
    v-for="param in data"
    :key="param.parameter.name"
  >
    <q-chip
      :label="param.parameter.name"
      :clickable="false"
      :ripple="false"
      square
      :color="getParamColor(param)"
    >
      <q-tooltip v-if="param.parameter.description">
        {{ param.parameter.description }}
      </q-tooltip>
    </q-chip>
    {{ param.value}}
  </div>
</template>

<script lang="ts">
import { Parameter } from 'src/models/experiment';
import { dtype_color_mapping, isValidDtype } from 'src/constants/mappings';

export default {
  name: 'DataTableParameter',
  components: {  },
  props: {
    data: {
      type: Object as () => Parameter[],
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

    function getParamColor(param: Parameter) {
      if (isValidDtype(param.parameter.dtype)) {
        return dtype_color_mapping[param.parameter.dtype];
      }
      return 'grey';
    }


    return {
      getParamColor,
    };
  }

};
</script>
