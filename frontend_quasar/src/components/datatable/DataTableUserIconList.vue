<template>
  <div
    class="tw-flex tw-items-center"
  >
    <div v-for="profile in data" :key="profile.user.username">
      <ProfileImage
        :profile=profile
        size="md"
        :tooltip=true
        :linkToProfile=true
      />
    </div>
  </div>
</template>

<script lang="ts">
import ProfileImage from 'components/ProfileImage.vue';
import { Profile } from 'src/models/experiment';
import { PropType } from 'vue';

export default {
  name: 'DataTableUserIconList',
  components: { ProfileImage },
  props: {
    data: {
      type: Object as PropType<Profile[]>,
      required: false,
    },
  },
};
</script>
