<template>
  <q-btn
    @mouseover="setHovering(true)"
    @mouseout="setHovering(false)"
    :color="(hovering && hoverColor !== undefined ? hoverColor : $attrs.color)"
    :icon="(hovering && hoverIcon !== undefined ? hoverIcon : $attrs.icon)"
    v-bind="$attrs"
  />
</template>

<script>
export default {
  name: 'HoverButton',
  props: {
    hoverColor: {
      type: String,
      required: false,
    },
    hoverIcon: {
      type: String,
      required: false,
    },
  },
  data() {
    return {
      hovering: false,
    };
  },
  methods: {
    setHovering(tf) {
      if (this.hovering !== tf) {
        this.hovering = tf;
      }
    },
  }
}
</script>
