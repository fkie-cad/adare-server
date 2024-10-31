<template>
  <q-card
    flat
  >
    <q-card-section>
      <div class="tw-text-5xl text-center q-pb-md">Welcome to ADARE</div>
      <div class="tw-text-xl text-center">The <b>A</b>utomated <b>D</b>esktop Forensic <b>A</b>nalysis tool for <b>R</b>eproducible <b>E</b>xperiments</div>
    </q-card-section>
    <q-separator />
    <q-card-section class="tw-flex tw-justify-evenly tw-flex-wrap">
      <StatisticCount
        icon="o_play_circle"
        name="Runs"
        :count="statsStore.stats.run_count"
        class="text-center q-ma-md"
        color="indigo-13"
      />
      <StatisticCount
        icon="o_science"
        name="Experiments"
        :count="statsStore.stats.experiment_count"
        class="text-center q-ma-md"
        color="teal-7"
      />
      <StatisticCount
        icon="o_hive"
        name="Testfunctions"
        :count="statsStore.stats.testfunction_count"
        class="text-center q-ma-md"
        color="purple-13"
      />
      <StatisticCount
        icon="o_person"
        name="Users"
        :count="statsStore.stats.user_count"
        class="text-center q-ma-md"
        color="red-13"
      />
      <StatisticCount
        icon="ion-git-pull-request"
        name="Requests"
        :count="statsStore.stats.request_count"
        class="text-center q-ma-md"
        color="orange-13"
      />
    </q-card-section>
    <q-separator />
    <q-card-section>
      <div class="tw-text-xl text-center">for access please write us a mail (mail@test.com)</div>
    </q-card-section>
  </q-card>
</template>

<script lang="ts">
import StatisticCount from 'components/global/StatisticCount.vue';
import {onMounted} from 'vue';
import {useStatsStore} from 'src/store/stats';

export default {
  name: 'WelcomeCard',
  components: {
    StatisticCount
  },
  setup(){
    const statsStore = useStatsStore()

    onMounted(() => {
      statsStore.fetchStats();
    })

    return {
      statsStore,
    }
  }
};
</script>
