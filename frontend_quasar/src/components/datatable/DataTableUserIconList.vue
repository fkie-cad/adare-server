<template>
  <div
    class="tw-flex tw-items-center"
  >
    <div v-for="user in data" :key="user.id">
      <ProfileImage
        :username=user.username
        size="md"
        :tooltip=true
        :linktoprofile=true
        :avatar="user.avatar"
      />
    </div>
  </div>
</template>

<script lang="ts">
import ProfileImage from 'components/ProfileImage.vue';

export default {
  name: 'DataTableUserIconList',
  components: { ProfileImage },
  props: {
    data: {
      type: Object,
      required: false,
    },
  },
};
</script>
