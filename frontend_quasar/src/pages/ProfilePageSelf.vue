<template>
  <q-page class="row items-center justify-evenly tw-overflow-visible" v-if="profile">
    <ProfileCard
      :profile="profile"
    />
  </q-page>
</template>

<script lang="ts">
import ProfileCard from 'components/ProfileCard.vue';
import { useUserStore } from 'src/store/user';
import { computed, onMounted } from 'vue';

export default {
  name: 'ProfilePage',
  components: {
    ProfileCard,
  },

  setup(){
    const userStore = useUserStore()
    const profile = computed(() => userStore.loggedInUserProfile)

    onMounted(async () => {
      await userStore.loadLoggedInUserProfile()
    })

    return {
      profile,
    };
  },

}
</script>

