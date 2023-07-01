<template>
  <q-page class="row items-center justify-evenly tw-overflow-visible">
    <ProfileCardSelf/>
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
import ProfileCardSelf from 'components/ProfileCardSelf.vue';


export default {
  name: 'ProfilePage',
  components: {
    ProfileCardSelf,
  },

}
</script>

