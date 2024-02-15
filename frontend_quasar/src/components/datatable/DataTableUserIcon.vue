<template>
  <div
    class="tw-flex tw-items-center"
  >
    <ProfileImage
      :username=data.username
      size="md"
      :tooltip=true
      :linktoprofile=true
      :avatar="data.avatar"
      v-if=data
    />
  </div>
</template>

<script lang="ts">
import ProfileImage from 'components/ProfileImage.vue';

export default {
  name: 'DataTableUserIcon',
  components: { ProfileImage },
  props: {
    data: {
      type: Object,
      required: false,
    },
    row: {
      type: Object,
      required: true,
    }
  },
};
</script>
