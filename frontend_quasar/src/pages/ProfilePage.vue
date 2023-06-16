<template>
  <q-page class="row items-center justify-evenly tw-overflow-visible">
    <ProfileCard />
    <q-card
      class="col-6"
    >
      <q-card-section>
        Maybe last activities
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script lang="ts">
import ProfileCard from 'components/ProfileCard.vue';

export default {
  name: 'ProfilePage',
  components: {
    ProfileCard,
  },
}
</script>

