<template>
  <ScopedTagBadge v-for="item in data" :key="item.name" :tag="item" />
</template>

<script lang="ts">
import { Tag } from 'src/models/experiment';
import ScopedTagBadge from 'src/components/global/ScopedTagBadge.vue';

export default {
  name: 'DataTableTags',
  components: { ScopedTagBadge },
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
  },
};
</script>
