<template>
    <StatusIcon :status="data.name"/>
</template>

<script lang="ts">
import StatusIcon from 'components/global/StatusIcon.vue';

export default {
  name: 'DataTableStatus',
  components: { StatusIcon },
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

};
</script>
