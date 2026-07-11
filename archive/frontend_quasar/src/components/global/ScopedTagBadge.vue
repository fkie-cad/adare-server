<template>
  <q-badge :color="tagColor" class="q-ma-xs">
    {{ tag.name }}
  </q-badge>
</template>

<script lang="ts">
import { defineComponent, computed, PropType } from 'vue';
import { Tag } from 'src/models/experiment';
import { getTagColor } from 'src/constants/tagColors';

export default defineComponent({
  name: 'ScopedTagBadge',
  props: {
    tag: {
      type: Object as PropType<Tag>,
      required: true,
    },
  },
  setup(props) {
    const tagColor = computed(() => getTagColor(props.tag.scope));

    return { tagColor };
  },
});
</script>
