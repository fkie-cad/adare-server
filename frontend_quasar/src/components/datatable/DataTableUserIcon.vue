<template>
  <div
    class="tw-flex tw-items-center"
  >
    <ProfileImage
      :profile="profile"
      size="md"
      :tooltip=true
      :linkToProfile=true
      v-if=profile
    />
  </div>
</template>

<script lang="ts">
import { computed, onMounted } from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import { useUserStore } from 'src/store/user';

export default {
  name: 'DataTableUserIcon',
  components: { ProfileImage },
  props: {
    data: {
      type: String,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    }
  },

  setup(props) {
    const userStore = useUserStore();
    const profile = computed(() => userStore.getProfile(props.data));

    onMounted(async () => {
      await userStore.fetchProfile(props.data);
    });

    return {
      profile,
    };
  }
};
</script>
