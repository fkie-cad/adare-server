<template>
  <div
    class="tw-flex tw-items-center"
  >
    <div v-for="user in data" :key="user.username">
      <ProfileImage
        :user=user
        size="md"
        :tooltip=true
        :linktoprofile=true
      />
    </div>
  </div>
</template>

<script lang="ts">
import ProfileImage from 'components/ProfileImage.vue';
import { User } from 'src/models/experiment';
import { PropType } from 'vue';

export default {
  name: 'DataTableUserIconList',
  components: { ProfileImage },
  props: {
    data: {
      type: Object as PropType<User[]>,
      required: false,
    },
  },
};
</script>
