<template>
  <q-timeline-entry
    v-bind="mergedProps"
    :class="{ dot: true, hide: hideDot }"
  >
    <!-- Forward Named Slots -->
    <template v-if="$slots.title" v-slot:title>
      <slot name="title"></slot>
    </template>

    <template v-if="$slots.subtitle" v-slot:subtitle>
      <slot name="subtitle"></slot>
    </template>

    <template v-if="$slots.icon" v-slot:icon>
      <slot name="icon"></slot>
    </template>

    <!-- Default Slot -->
    <slot></slot>
  </q-timeline-entry>
</template>

<script setup>
import { computed, useAttrs } from 'vue';
import { colors } from 'quasar';

const props = defineProps({
  title: String,
  subtitle: String,
  icon: String,
  dotColor: { type: String, required: true },
  lineColor: { type: String, required: true },
  hideDot: { type: Boolean, default: false },
});

// Access Slots to Check if They Exist
// Access attributes and slots
const attrs = useAttrs();

// Merge props and $attrs dynamically
const mergedProps = computed(() => ({
  ...props, // Spread all defined props
  ...attrs, // Spread all additional attributes
}));

// Compute actual colors
const dotColorValue = computed(() => colors.getPaletteColor(props.dotColor));
const lineColorValue = computed(() => colors.getPaletteColor(props.lineColor));
</script>

<style scoped>
/* Apply dot color */
.q-timeline__entry.dot >>> .q-timeline__dot::before {
  background-color: v-bind(dotColorValue);
}

/* Apply line color */
.q-timeline__entry.dot >>> .q-timeline__dot::after {
  background-color: v-bind(lineColorValue);
}

/* Hide the dot */
.q-timeline__entry.hide >>> .q-timeline__dot::before {
  display: none;
}
</style>
