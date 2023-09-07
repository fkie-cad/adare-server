<template>
  <q-card
    flat
  >
    <q-card-section>
      <div class="tw-text-5xl text-center q-pb-md">Welcome to ADARE</div>
      <div class="tw-text-xl text-center">The Automated Desktop Forensic Analysis tool for Reproducible Experiments</div>
    </q-card-section>
    <q-separator />
    <q-card-section class="tw-flex tw-justify-evenly tw-flex-wrap">
      <StatisticCount
        icon="o_hive"
        name="Scenarios"
        :count="scenario_count"
        class="text-center q-ma-md"
        color="deep-purple-13"
      />
      <StatisticCount
        icon="o_science"
        name="Experiment"
        :count="experiment_count"
        class="text-center q-ma-md"
        color="indigo-13"
      />
      <StatisticCount
        icon="o_play_circle"
        name="Experiment Run"
        :count="experiment_run_count"
        class="text-center q-ma-md"
        color="teal-7"
      />
      <StatisticCount
        icon="o_person"
        name="Users"
        :count="user_count"
        class="text-center q-ma-md"
        color="orange-13"
      />
      <StatisticCount
        icon="ion-git-pull-request"
        name="Requests"
        :count="request_count"
        class="text-center q-ma-md"
        color="red-13"
      />
    </q-card-section>
    <q-separator />
    <q-card-section>
      <div class="tw-text-xl text-center">for access please write us a mail (mail@test.com)</div>
    </q-card-section>
  </q-card>
</template>

<script lang="ts">
import API from 'src/api/';
import StatisticCount from 'components/global/StatisticCount.vue';
import {onMounted, ref} from 'vue';
import axios from 'axios';

export default {
  name: 'WelcomeCard',

  components: {
    StatisticCount
  },

  setup(){
    let experiment_count = ref<number>(0);
    let scenario_count = ref<number>(0);
    let experiment_run_count = ref<number>(0);
    let user_count = ref<number>(0);
    let request_count = ref<number>(0);

    async function LoadStatistics(){
      await axios.get(API.API + 'statistics/')
        .then((response) => {
          experiment_count.value = response.data.experiment_count
          scenario_count.value = response.data.scenario_count
          experiment_run_count.value = response.data.experiment_run_count
          user_count.value = response.data.user_count
          request_count.value = response.data.request_count
        })
    }

    onMounted(() => {
      LoadStatistics()
    })

    return {
      experiment_count,
      scenario_count,
      experiment_run_count,
      user_count,
      request_count,
    }
  }



};
</script>
