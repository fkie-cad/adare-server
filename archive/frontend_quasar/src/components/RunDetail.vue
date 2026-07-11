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
          <div class="col"><StatusIcon :status="run.result_status.name" size="xl"/></div>
          <div class="col tw-text-right">{{ secondsToString(run.duration) }}</div>
        </div>
      </q-card-section>
      <q-card-section>
        <q-card>
          <q-card-section class="text-h5 ">
            Events
            <q-toggle label="Only show tests" v-model="onlyShowTests" />
          </q-card-section>
          <q-card-section>
            <q-timeline
              class="q-pa-md"
            >
              <CustomQTimelineEntry
                v-for="event in events"
                :key="event.ulid"
                :dot-color="getDotColor(event)"
                :line-color="getLineColor(event)"
                :icon="getIcon(event)"
                class="nonopaque dense"
              >
                <template v-slot:subtitle>
                  <div class="tw-text-base tw-font-normal tw-normal-case text-black tw-opacity-100">
                    <span v-if="isGuiFindEvent(event)">
                      find: <i>{{ event.objective }}</i> -> {{event.positions}}
                    </span>
                    <span v-if="isGuiClickEvent(event)">
                      click at: <i>{{ event.target }}</i>
                    </span>
                    <span v-if="isGuiKeypressEvent(event)">
                      press: <i>{{ event.keys }}</i>
                    </span>
                    <span v-if="isCommandEvent(event)">
                      command: <i>{{ event.command }}</i>
                    </span>
                    <span v-if="isTestEvent(event)">
                      test: <i>{{ event.abstracttest.name }}</i> ({{ event.abstracttest.testfunction.name }})
                    </span>
                  </div>
                </template>
                <div >
                  toogle this
                </div>
              </CustomQTimelineEntry>
            </q-timeline>
          </q-card-section>
        </q-card>
      </q-card-section>
    </q-card>
  </div>
</template>


<script lang="ts">
import { useRunStore } from 'src/store/run';
import { useUserStore } from 'src/store/user';
import { useRunEventStore } from 'src/store/runevent';
import { computed, onMounted, ref } from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import StatusIcon from 'components/global/StatusIcon.vue';
import CustomQTimelineEntry from 'components/global/CustomQTimelineEntry.vue';
import {
  isGuiIdleEvent,
  Event,
  isGuiFindEvent,
  isGuiClickEvent,
  isGuiKeypressEvent,
  isCommandEvent, isErrorEvent, isTestEvent
} from 'src/models/experiment';

export default {
  name: 'RunDetail',

  components: { CustomQTimelineEntry, StatusIcon, ProfileImage },

  props: {
    ulid: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const runStore = useRunStore()
    const userStore = useUserStore()
    const runEventStore = useRunEventStore()
    const run = computed(() => runStore.getRun(props.ulid))
    const profile = computed(() => userStore.getProfile(run.value.published_by));
    const onlyShowTests = ref<boolean>(false)
    const events = computed(() => {
      if (onlyShowTests.value) {
        return Array.isArray(run.value.events) ? run.value.events.filter(event => isTestEvent(event)) : [];
      }
      return Array.isArray(run.value.events) ? run.value.events.filter(event => !isGuiIdleEvent(event)) : [];
    })

    function secondsToString(seconds: number){
      // round to nearest second
      seconds = Math.round(seconds);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}min ${remainingSeconds}s`;
    }

    onMounted(async () => {
      await runStore.fetchRun(props.ulid)
      await runEventStore.setRun(props.ulid)
      await userStore.fetchProfile(run.value.published_by)
    })

    function getDotColor(event: Event){
      if (isTestEvent(event)){
        if(event.result.status.name === 'success'){
          return 'positive'
        } else if(event.result.status.name  === 'failed'){
          return 'negative'
        }
      }
      return 'blue-grey-6'
    }

    function getLineColor(event: Event){
      if (isGuiFindEvent(event)){
        return 'positive'
      }
      return 'positive'
    }

    function getIcon(event: Event){
      if (isGuiFindEvent(event)){
        return 'search'
      } else if (isGuiClickEvent(event)){
        return 'mouse'
      } else if (isGuiIdleEvent(event)){
        return 'pause'
      } else if (isGuiKeypressEvent(event)){
        return 'keyboard'
      } else if (isCommandEvent(event)){
        return 'code'
      } else if (isErrorEvent(event)){
        return 'error'
      } else if (isTestEvent(event)){
        return 'quiz'
      }
      return ''
    }

    return {
      run,
      profile,
      runEventStore,
      secondsToString,
      isGuiIdleEvent,
      isGuiClickEvent,
      isTestEvent,
      isGuiKeypressEvent,
      isCommandEvent,
      isGuiFindEvent,
      getDotColor,
      getLineColor,
      getIcon,
      events,
      onlyShowTests
    }
  }
}

</script>

<style scoped>
.q-timeline__entry.nonopaque >>> .q-timeline__subtitle {
  opacity: 1;
}

.q-timeline__entry.dense >>> .q-timeline__content {
  padding-bottom: 0.1rem;
}

</style>
