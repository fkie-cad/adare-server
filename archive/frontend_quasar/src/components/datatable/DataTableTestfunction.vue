<template>
   {{data.set}}.{{ data.name }}
</template>

<script lang="ts">
import { Testfunction } from 'src/models/experiment';

export default {
  name: 'DataTableTestfunction',
  components: {  },
  props: {
    data: {
      type: Object as () => Testfunction,
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

    return {
    };
  }

};
</script>
