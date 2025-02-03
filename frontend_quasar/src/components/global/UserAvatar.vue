<template>
  <div
    class="tw-rounded-full bg-secondary flex justify-center items-center"
    :style="{ width: width, height: height }"
  >
    <q-img
      :src="profile.avatar"
      class="object-cover"
      spinner-color="primary"
      img-class="tw-rounded-full"
    >
      <template v-slot:error>
        <span
          class="text-white full-width full-height flex justify-center items-center"
          :style="{ fontSize: fontSize }"
        >
          {{ profile.user.username.charAt(0).toUpperCase() }}
        </span>
      </template>
    </q-img>
    <q-tooltip v-if="tooltip">
        {{ profile.user.username }}
    </q-tooltip>
  </div>
</template>

<script lang="ts">
import { ref, computed, defineComponent, PropType } from 'vue'
import { SizeType, isValidSizeType } from 'src/constants';
import { Profile } from 'src/models/experiment';

export default defineComponent({
  name: 'UserAvatar',

  props: {
    profile: {
      type: Object as PropType<Profile>,
      required: true,
    },
    size: {
      type: String as PropType<SizeType>, // Ensure `size` prop uses the `SizeType`
      default: 'md',
      validator: (value: string) => isValidSizeType(value), // Validate `size` prop value
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
  },

  setup(props) {
    // Ensure that size is one of 'sm', 'md', or 'lg'
    const validSizes: Array<'sm' | 'md' | 'lg'> = ['sm', 'md', 'lg'];
    const size = ref(validSizes.includes(props.size) ? props.size : 'md');

    // Mappings for width and font size based on size
    const sizeToWidth: Record<'sm' | 'md' | 'lg', string> = {
      sm: '30px',
      md: '50px',
      lg: '100px',
    };

    const sizeToFontSize: Record<'sm' | 'md' | 'lg', string> = {
      sm: '10px',
      md: '20px',
      lg: '40px',
    };

    // Computed properties for width, height, and font size
    const width = computed(() => sizeToWidth[size.value]);
    const height = computed(() => sizeToWidth[size.value]);
    const fontSize = computed(() => sizeToFontSize[size.value]);

    return {
      fontSize,
      width,
      height,
    };
  },
});
</script>

