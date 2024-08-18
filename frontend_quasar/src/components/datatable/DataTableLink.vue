<template>
  <q-btn
    :color="vars.color"
    :icon="vars.icon"
    @click="OpenInNewTab(data)"
    class="q-px-sm q-mx-sm"
  >
    <q-tooltip v-if="vars.tooltip">{{ vars.tooltip }}</q-tooltip>
  </q-btn>
</template>

<script lang="ts">
import { TypeVarsLink } from 'src/datatypes/quasar_extensions';

const defaultTypeVarsLink: TypeVarsLink = {
  icon: 'get_app',
  tooltip: '',
  color: 'primary',
};

export default {
  name: 'DataTableLink',
  components: {  },
  props: {
    data: {
      type: String,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
    col: {
      type: Object,
      required: true,
    }
  },

  setup(props) {

    function OpenInNewTab(url: string){
      window.open(url, '_blank')
    }

    // check if row.typeVarsLink is defined, if not use defaultTypeVarsLink
    const vars = Object.assign({}, defaultTypeVarsLink, props.col.typeVarsLink);

    return {
      OpenInNewTab,
      vars,
    };
  }
};
</script>
