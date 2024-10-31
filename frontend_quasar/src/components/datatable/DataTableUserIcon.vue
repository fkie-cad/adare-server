<template>
  <div
    class="tw-flex tw-items-center"
  >
    <ProfileImage
      :user="data"
      size="md"
      :tooltip=true
      :linktoprofile=true
      v-if=data
    />
  </div>
</template>

<script lang="ts">
import { PropType } from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import { User } from 'src/models/experiment';

export default {
  name: 'DataTableUserIcon',
  components: { ProfileImage },
  props: {
    data: {
      type: Object as PropType<User>,
      required: false,
    },
    row: {
      type: Object,
      required: true,
    }
  },
};
</script>
