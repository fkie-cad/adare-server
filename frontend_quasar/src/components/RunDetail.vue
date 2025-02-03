<template>
  <div>
    <q-card v-if="run">
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">ulid</div>
          <div class="col tw-text-right">published by</div>
        </div>
        <div class="row tw-text-3xl">
          <div class="col">{{run.ulid}}</div>
          <div class="col tw-text-right flex justify-end">
            <ProfileImage
              :profile="profile"
              size="md"
              :tooltip=true
              :linkToProfile=true
              v-if=profile
            /></div>
        </div>
      </q-card-section>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">experiment</div>
          <div class="col tw-text-right">environment</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{run.experiment}}</div>
          <div class="col tw-text-right">{{run.environment}}</div>
        </div>
      </q-card-section>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">result status</div>
          <div class="col tw-text-right">duration</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{run.result_status}}</div>
          <div class="col tw-text-right">{{ secondsToString(run.duration) }}</div>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>


<script lang="ts">
import { useRunStore } from 'src/store/run';
import { useUserStore } from 'src/store/user';
import { computed, onMounted, } from 'vue';
import ProfileImage from 'components/ProfileImage.vue';

export default {
  name: 'RunDetail',

  components: { ProfileImage },

  props: {
    ulid: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const runStore = useRunStore()
    const userStore = useUserStore()
    const run = computed(() => runStore.getRun(props.ulid))
    const profile = computed(() => userStore.getProfile(run.value.published_by));

    function secondsToString(seconds: number){
      // round to nearest second
      seconds = Math.round(seconds);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}min ${remainingSeconds}s`;
    }

    onMounted(async () => {
      await runStore.fetchRun(props.ulid)
      await userStore.fetchProfile(run.value.published_by)
    })

    return {
      run,
      profile,
      secondsToString,
    }
  }
}

</script>
