<template>
  <q-badge v-for="item in data" :key="item" color="primary" class="q-ma-xs">
    #{{ item }}
  </q-badge>
</template>

<script lang="ts">

export default {
  name: 'DataTableTags',
  components: {  },
  props: {
    data: {
      type: Array,
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
