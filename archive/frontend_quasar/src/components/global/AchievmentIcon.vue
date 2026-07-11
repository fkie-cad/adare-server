<template>
  <div>
    <q-avatar
      :src="image"
      size="110px"
      class="row"
    >
      <img :src="image" style="height: 110px; width: 110px" class="q-pt-none q-mt-none" alt=""/>
      <q-badge
        color="accent"
        floating
        :label="count"
        v-if="count"
      />
      <q-tooltip>
        {{ description }}
      </q-tooltip>
    </q-avatar>
  </div>

</template>

<script lang="ts">


export default {
  name: 'AchievementIcon',
  props: {
    image: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: true,
    },
    count: {
      type: Number,
      required: false,
    },
  },

}

</script>
