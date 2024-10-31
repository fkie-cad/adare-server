<template>
  <q-badge v-for="item in data" :key="item.name" :color="vars.color" class="q-ma-xs">
    #{{ item }}
  </q-badge>
</template>

<script lang="ts">
import { TypeVarsTag } from 'src/models/quasar_extensions';
import { Tag } from 'src/models/experiment';

const defaultTypeVarsTag: TypeVarsTag = {
  color: 'primary',
};

export default {
  name: 'DataTableTags',
  components: {  },
  props: {
    data: {
      type: Array as () => Tag[],
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
    color: {
      type: String,
      default: 'primary',
    },
  },

  setup(props) {

    // check if row.typeVarsLink is defined, if not use defaultTypeVarsLink
    const vars = Object.assign({}, defaultTypeVarsTag, props.col.typeVarsTag);

    return {
      vars,
    };
  }

};
</script>
