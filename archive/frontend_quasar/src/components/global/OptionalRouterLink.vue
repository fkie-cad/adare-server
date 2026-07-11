<template>
  <router-link
    v-if="!disabled"
    v-bind="$attrs"
  >
    <slot/>
  </router-link>

  <span
    v-else
    v-bind="$attrs"
  >
    <slot/>
  </span>
</template>

<script>
export default {
  name: 'OptionalRouterLink',

  props: {
    params: Object,
    disabled: {
      type: Boolean,
      default: false,
    },
  },
};
</script>
