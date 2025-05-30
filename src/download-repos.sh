#!/bin/bash
# script that downloads appropriate repos

mkdir -p pulp-platform
cd pulp-platform
git clone --recursive https://github.com/pulp-platform/pulp-freertos                     
cd pulp-freertos                                                 
git checkout 1f333de
git branch develop
git checkout develop
cd ..

git clone --recursive --branch renzo-isa https://github.com/pulp-platform/pulp-riscv-gnu-toolchain                                                                                
cd pulp-riscv-gnu-toolchain                                      
git checkout 5d39fed                                                                     
git branch develop
git checkout develop
cd ..

git clone --recursive https://github.com/pulp-platform/pulp-runtime/                     
cd pulp-runtime                                                  
git checkout a39271c                                                                     
git branch develop
git checkout develop
cd ..
                                                                                          
# pulpissimo                                                                                 
git clone --recursive https://github.com/pulp-platform/pulpissimo                        
cd pulpissimo                                                    
git checkout 1045d39                                                                     
git branch develop
git checkout develop
cd ..
                                                                                          
git clone --recursive https://github.com/pulp-platform/pulp-runtime-examples             
cd pulp-runtime-examples                                         
git checkout 4391c68                                                                     
git branch develop
git checkout develop
cd ..


git clone --recursive https://github.com/pulp-platform/pulp-freertos                     
cd pulp-freertos                                                 
git checkout 1f333de
git branch develop
git checkout develop
cd ..
