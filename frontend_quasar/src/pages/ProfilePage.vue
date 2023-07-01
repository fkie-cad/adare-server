<template>
  <q-page class="row items-center justify-evenly tw-overflow-visible">
    <ProfileCard :username="username"/>
  </q-page>

</template>

<script lang="ts">
import ProfileCard from 'components/ProfileCard.vue';

export default {
  name: 'ProfilePage',
  props: ['username'],
  components: {
    ProfileCard,
  },

}
</script>

