import {mkdtemp,mkdir,writeFile,readFile} from 'node:fs/promises'
import {join} from 'node:path'
const pkg='/private/tmp/rein-production-20260914'
const fixture=await readFile(join(pkg,'fixtures/cases/prerequisites.json'),'utf8')
for(const variant of ['AZURE','OCHRE']){
 const root=await mkdtemp('/private/tmp/rein-ch05-production-rereview-1/demo-ts-')
 await mkdir(join(root,'ts'));await mkdir(join(root,'fixtures/workspaces/prerequisites'),{recursive:true});await mkdir(join(root,'fixtures/cases'),{recursive:true})
 await writeFile(join(root,'fixtures/cases/prerequisites.json'),fixture)
 await writeFile(join(root,'fixtures/workspaces/prerequisites/README.md'),`marker: ${variant} README`)
 await writeFile(join(root,'fixtures/workspaces/prerequisites/extra.md'),`marker: ${variant} extra`)
 process.chdir(join(root,'ts'));process.argv=['node','ch05-loop.ts']
 console.log(JSON.stringify({variant,root}))
 await import(`${pkg}/ts/examples/ch05-loop.ts?variant=${variant}`)
}
