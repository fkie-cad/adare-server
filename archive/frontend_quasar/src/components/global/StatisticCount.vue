<template>
  <div class="col text-center">
      <div class="text-h6 q-py-md text-no-wrap" :class="'text-'+color">{{ name }}</div>
      <q-icon :name="icon" size="5em" :color="color"/>
      <div class="text-h4 q-py-md" :class="'text-'+color">{{ count }}</div>
    </div>
</template>

<script lang="ts">

export default {
  props: {
    icon: {
      type: String,
    },
    name: {
      type: String,
    },
    count: {
      type: Number,
    },
    color: {
      type: String,
      default: 'black',
    },
  },

}

</script>
