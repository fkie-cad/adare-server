<template>
  <q-badge color="positive" class="q-ma-sm">
    {{ data.successful }}
  </q-badge>
  <q-badge color="negative" class="q-ma-sm">
    {{ data.failed }}
  </q-badge>
</template>

<script lang="ts">

export default {
  name: 'DataTableRunCounts',
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

};
</script>
