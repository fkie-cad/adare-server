<template>
  <div
    class="tw-rounded-full bg-secondary flex justify-center items-center"
    :style="{ width: size_to_width[size], height: size_to_width[size] }"
  >
    <q-img
      :src="img"
      class="object-cover"
      spinner-color="primary"
      img-class="tw-rounded-full"
    >
      <template v-slot:error>
        <span
          class="text-white full-width full-height flex justify-center items-center"
          :style="{ fontSize: size_to_font_size[size] }"
        >
          {{ username.charAt(0).toUpperCase() }}
        </span>
      </template>
    </q-img>
    <q-tooltip v-if="tooltip">
        {{ username }}
    </q-tooltip>
  </div>
</template>

<script lang="ts">

export default {
  name: 'UserAvatar',

  props: {
    img: {
      type: String,
    },
    username: {
      type: String,
    },
    size: {
      type: String,
      default: 'md'
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
  },

  setup(props) {
    const size_to_width = {
      'sm': '30px',
      'md': '50px',
      'lg': '100px',
    }

    const size_to_font_size = {
      'sm': '10px',
      'md': '20px',
      'lg': '40px',
    }

    return {
      size_to_width,
      size_to_font_size,
    }

  }
}
</script>
