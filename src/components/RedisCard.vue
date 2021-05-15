<template>
  <v-card
      class="pa-2"
  > <v-card-title>
    People in frame: {{people.numberOfPeople}}
  </v-card-title>

    <trend
            :data="peopleArray"
            :gradient="['#6fa8dc', '#42b983', '#2c3e50']"
            auto-draw
            smooth
            style="height: 100%"
    >
    </trend>
  </v-card>
</template>

<script>

  export default {
    name: 'RedisCard',
    data: () => ({
      people: {
        numberOfPeople: '0'
      },
      peopleArray: [],
      pollInterval: null
    }),
    methods: {
      async updatePeople () {
        try{
          const response = await fetch('http://localhost:5000/peoplestream');
          if (!response.ok) {
            const message = `An error has occured: ${response.status}`;
            throw new Error(message);
          }
          const people = await response.json();
          this.people = people
          this.peopleArray.push(parseInt(people['numberOfPeople']))
          if(this.peopleArray.length > 60)
            this.peopleArray = this.peopleArray.slice(this.peopleArray.length - 60)
        }
        catch (e) {
          console.log(e)
        }
      }
    },
    beforeDestroy () {
      clearInterval(this.pollInterval)
    },
    created () {
      this.pollInterval = setInterval(this.updatePeople, 1000)
    }
  }
</script>
